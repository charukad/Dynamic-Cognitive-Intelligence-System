import { create } from 'zustand';

type ViewType = 'orbit' | 'cortex' | 'neural-link' | 'conductor' | 'settings';

interface UIStore {
    activeView: ViewType;
    setActiveView: (view: ViewType) => void;

    isSidebarCollapsed: boolean;
    toggleSidebar: () => void;

    settings: {
        showStats: boolean;
        enablePostProcessing: boolean;
        lowPowerMode: boolean;
    };
    toggleSetting: (setting: 'showStats' | 'enablePostProcessing' | 'lowPowerMode') => void;
}

export const useUIStore = create<UIStore>((set) => ({
    activeView: 'orbit',
    setActiveView: (view) => set({ activeView: view }),

    isSidebarCollapsed: true,
    toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

    settings: {
        showStats: true,
        enablePostProcessing: true,
        lowPowerMode: false
    },
    toggleSetting: (key) => set((state) => ({
        settings: { ...state.settings, [key]: !state.settings[key] }
    }))
}));
