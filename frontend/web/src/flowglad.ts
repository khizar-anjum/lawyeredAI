import { FlowgladServer } from '@flowglad/nextjs/server';
import { createClient } from '@/utils/supabase/server';

export const flowgladServer = new FlowgladServer({
  supabaseAuth: {
    client: createClient, // lets Flowglad know who the current user is (via Supabase cookies)
  },
  // If you have org customers instead of individuals, see getRequestingCustomer() pattern.
});
