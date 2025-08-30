import './globals.css';
import type { Metadata } from 'next';
import { createClient } from '@/utils/supabase/server';
import { FlowgladProvider } from '@flowglad/nextjs';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Lawyered Access',
  description: 'Auth + Billing gateway for Lawyered',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <html lang="en">
      <body>
        <nav style={{ padding: '12px', borderBottom: '1px solid #eee' }}>
          <Link href="/">Home</Link>
          <span style={{ marginLeft: 16 }} />
          {user ? <Link href="/billing">Billing</Link> : <Link href="/sign-in">Sign In</Link>}
        </nav>

        <FlowgladProvider loadBilling={!!user}>
          {children}
        </FlowgladProvider>
      </body>
    </html>
  );
}
