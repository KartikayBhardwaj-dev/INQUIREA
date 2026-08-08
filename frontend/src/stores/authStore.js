"use client";

import { create } from "zustand";

const useAuthStore = create((set) => ({
  user: null,
  isLoggedIn: false,
  isLoading: true,

  setUser: (user) =>
    set({
      user,
      isLoggedIn: true,
      isLoading: false,
    }),

  clearUser: () =>
    set({
      user: null,
      isLoggedIn: false,
      isLoading: false,
    }),

  setLoading: (isLoading) =>
    set({
      isLoading,
    }),
}));

export default useAuthStore;