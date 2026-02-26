import { TournamentBracket } from "@/components/gaia/TournamentBracket";

export default function TournamentsPage() {
  return (
    <div className="h-full min-h-full p-4 md:p-6">
      <TournamentBracket tournamentId="latest" />
    </div>
  );
}
