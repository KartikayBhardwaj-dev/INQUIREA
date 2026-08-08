import { create } from "zustand";

const useAppStore = create((set) => ({
  sidebarOpen: true,

  toggleSidebar: () =>
    set((state) => ({
      sidebarOpen: !state.sidebarOpen,
    })),
}));

export default useAppStore;