import { useQueryRAGMutation } from '@/infrastructure/store/api/apiSlice';

export const useRAGQuery = () => {
  const [trigger, result] = useQueryRAGMutation();

  return {
    mutate: trigger,
    mutateAsync: trigger,
    ...result,
    isPending: result.isLoading,
  };
};
