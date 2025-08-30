'use client';

import { useState } from 'react';
import { useRouter, useSearchParams, Link } from 'next/navigation';
import { createClient } from '@/utils/supabase/client';

export default function SignIn() {
  const supabase = createClient();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) return alert(error.message);
    router.push('/billing'); // go to billing to subscribe
  }

  return (
    <main style={{ maxWidth: 440, margin: '48px auto' }}>
      <h1>Sign in</h1>
      <form onSubmit={onSubmit}>
        <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button type="submit">Sign in</button>
      </form>
      <p>New here? <a href="/sign-up">Create an account</a></p>
    </main>
  );
}
