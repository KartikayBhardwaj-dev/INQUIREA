"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getEmailIntelligence,
  syncEmails,
} from "../services/intelligence.service";


export function useEmailIntelligence() {
  return useQuery({
    queryKey: ["email-intelligence"],
    queryFn: getEmailIntelligence,
    staleTime: 30 * 1000,
  });
}


export function useSyncEmails() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => syncEmails(7),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["email-intelligence"],
      });
    },
  });
}