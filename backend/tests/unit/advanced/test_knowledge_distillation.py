"""Tests for knowledge distillation system."""

import pytest

from src.services.advanced.knowledge_distillation import (
    DistillationExample,
    KnowledgeDistiller,
    StudentModel,
    TeacherModel,
)


@pytest.mark.asyncio
class TestKnowledgeDistillation:
    """Test suite for knowledge distillation."""

    async def test_teacher_model_generation(self):
        """Test teacher model generation."""
        teacher = TeacherModel(model_name="gpt-4")
        
        result = await teacher.generate(
            prompt="Explain recursion",
            max_tokens=100,
        )
        
        assert "output" in result
        assert "confidence" in result
        assert result["confidence"] > 0

    async def test_student_model_initialization(self):
        """Test student model initialization."""
        student = StudentModel(model_name="phi-3-mini")
        
        assert student.model_name == "phi-3-mini"
        assert len(student.training_examples) == 0

    async def test_add_training_example(self):
        """Test adding training examples."""
        student = StudentModel()
        
        example = DistillationExample(
            input_text="What is Python?",
            teacher_output="Python is a programming language.",
            teacher_confidence=0.95,
        )
        
        student.add_training_example(example)
        
        assert len(student.training_examples) == 1
        assert student.training_examples[0].input_text == "What is Python?"

    async def test_student_training(self):
        """Test student model training."""
        student = StudentModel()
        
        # Add examples
        for i in range(10):
            example = DistillationExample(
                input_text=f"Question {i}",
                teacher_output=f"Answer {i}",
            )
            student.add_training_example(example)
        
        result = await student.train(epochs=2, batch_size=4)
        
        assert result["status"] == "completed"
        assert result["examples"] == 10
        assert result["epochs"] == 2

    async def test_distiller_initialization(self):
        """Test distiller initialization."""
        teacher = TeacherModel()
        student = StudentModel()
        distiller = KnowledgeDistiller(teacher, student, temperature=2.0)
        
        assert distiller.teacher == teacher
        assert distiller.student == student
        assert distiller.temperature == 2.0

    async def test_distill_task(self):
        """Test task distillation."""
        teacher = TeacherModel()
        student = StudentModel()
        distiller = KnowledgeDistiller(teacher, student)
        
        examples = await distiller.distill_task(
            task_description="Summarize the following text",
            input_examples=[
                "Long text 1",
                "Long text 2",
                "Long text 3",
            ],
        )
        
        assert len(examples) == 3
        assert len(distiller.distilled_examples) == 3
        assert len(student.training_examples) == 3

    async def test_distill_agent_behavior(self):
        """Test agent behavior distillation."""
        teacher = TeacherModel()
        student = StudentModel()
        distiller = KnowledgeDistiller(teacher, student)
        
        task_samples = [
            {"input": "Write a function to sum numbers"},
            {"input": "Debug this code"},
        ]
        
        examples = await distiller.distill_agent_behavior(
            agent_type="coder",
            task_samples=task_samples,
        )
        
        assert len(examples) == 2
        assert all(ex.metadata["task"].startswith("You are a coder") for ex in examples)

    async def test_distillation_example_metadata(self):
        """Test metadata in distillation examples."""
        example = DistillationExample(
            input_text="Test input",
            teacher_output="Test output",
            metadata={"source": "test", "task": "testing"},
        )
        
        assert example.metadata["source"] == "test"
        assert example.metadata["task"] == "testing"

    async def test_distiller_statistics(self):
        """Test distiller statistics."""
        teacher = TeacherModel(model_name="gpt-4")
        student = StudentModel(model_name="phi-3")
        distiller = KnowledgeDistiller(teacher, student)
        
        # Add some examples
        await distiller.distill_task(
            task_description="Test task",
            input_examples=["Ex 1", "Ex 2"],
        )
        
        stats = distiller.get_statistics()
        
        assert stats["teacher_model"] == "gpt-4"
        assert stats["student_model"] == "phi-3"
        assert stats["total_examples"] == 2
        assert "avg_confidence" in stats

    async def test_confidence_tracking(self):
        """Test confidence tracking in distillation."""
        teacher = TeacherModel()
        student = StudentModel()
        distiller = KnowledgeDistiller(teacher, student)
        
        await distiller.distill_task(
            task_description="Test",
            input_examples=["Test 1", "Test 2", "Test 3"],
        )
        
        # Check confidence values
        confidences = [ex.teacher_confidence for ex in distiller.distilled_examples]
        assert all(0 <= c <= 1 for c in confidences)
        assert len(confidences) == 3

    async def test_multiple_tasks_distillation(self):
        """Test distilling multiple tasks."""
        teacher = TeacherModel()
        student = StudentModel()
        distiller = KnowledgeDistiller(teacher, student)
        
        # Distill first task
        await distiller.distill_task(
            task_description="Task 1",
            input_examples=["Input 1", "Input 2"],
        )
        
        # Distill second task
        await distiller.distill_task(
            task_description="Task 2",
            input_examples=["Input 3", "Input 4"],
        )
        
        assert len(distiller.distilled_examples) == 4
        assert len(student.training_examples) == 4

    async def test_temperature_effect(self):
        """Test different distillation temperatures."""
        teacher = TeacherModel()
        student1 = StudentModel()
        student2 = StudentModel()
        
        distiller_low_temp = KnowledgeDistiller(teacher, student1, temperature=1.0)
        distiller_high_temp = KnowledgeDistiller(teacher, student2, temperature=5.0)
        
        assert distiller_low_temp.temperature == 1.0
        assert distiller_high_temp.temperature == 5.0

    async def test_empty_student(self):
        """Test student with no training examples."""
        student = StudentModel()
        
        result = await student.train(epochs=1)
        
        assert result["examples"] == 0
        assert result["status"] == "completed"

    async def test_distillation_example_defaults(self):
        """Test distillation example default values."""
        example = DistillationExample(
            input_text="Test",
            teacher_output="Output",
        )
        
        assert example.teacher_logits is None
        assert example.teacher_confidence == 1.0
        assert example.metadata == {}
