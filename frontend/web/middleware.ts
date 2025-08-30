import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_PATHS = [
  '/sign-in',
  '/sign-up',
  '/billing',
  '/api/flowglad',        // Flowglad needs this open
  '/favicon.ico',
  '/_next',
  '/assets',
];

function isPublic(pathname: string) {
  return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p));
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (isPublic(pathname)) {
    return NextResponse.next();
  }

  // Check Supabase session via cookie presence (quick heuristic).
  const hasSupabaseCookie =
    req.cookies.get('sb:token') ||
    req.cookies.get('sb-access-token') ||
    req.cookies.get('supabase-auth-token');

  if (!hasSupabaseCookie) {
    const url = req.nextUrl.clone();
    url.pathname = '/sign-in';
    url.searchParams.set('next', pathname);
    return NextResponse.redirect(url);
  }

  // Require active subscription: call Flowglad API route to get status
  try {
    const res = await fetch(new URL('/api/flowglad/customer', req.nextUrl.origin), {
      headers: { cookie: req.headers.get('cookie') || '' },
    });

    if (res.ok) {
      const data = await res.json();
      // This shape may vary; look for an 'active' subscription.
      const hasActive =
        !!data?.subscriptions?.find((s: any) => (s.status || '').toLowerCase() === 'active') ||
        !!data?.activeSubscription ||
        !!data?.plan?.active;

      if (hasActive) return NextResponse.next();
    }
  } catch {}

  // No active sub → redirect to billing
  const to = req.nextUrl.clone();
  to.pathname = '/billing';
  return NextResponse.redirect(to);
}

export const config = {
  matcher: ['/((?!api/flowglad).*)'], // run for all routes except flowglad api
};
