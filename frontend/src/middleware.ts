import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const publicPaths = ["/auth/login", "/auth/signup", "/auth/register-seller"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get("access_token")?.value;

  // Allow public paths
  if (publicPaths.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  // Redirect to login if no token
  if (!accessToken) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // For role-based routes, we'd need to decode the token
  // This is a simple check - the actual role verification happens in the components
  // since we can't easily decode JWT in middleware without the secret

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/buyer/:path*",
    "/seller/:path*",
    "/admin/:path*",
  ],
};