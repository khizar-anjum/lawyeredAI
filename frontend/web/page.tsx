import Link from 'next/link';

export default async function Home() {
  const appUrl = process.env.NEXT_PUBLIC_APP_BASE_URL || 'http://localhost:8000';
  return (
    <main style={{ maxWidth: 720, margin: '64px auto', textAlign: 'center' }}>
      <h1>Welcome to Lawyered</h1>
      <p>Your subscription is active. Launch the app below.</p>
      <a href={appUrl} target="_blank" rel="noreferrer">
        <button style={{ padding: '12px 20px', fontSize: 16 }}>Launch Lawyered App</button>
      </a>
      <p style={{ marginTop: 24 }}><a href="/billing">Manage billing</a></p>
    </main>
  );
}
