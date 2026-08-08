"use client";

export default function GoogleLoginButton() {
  function handleLogin() {
    window.location.href =
      `${process.env.NEXT_PUBLIC_API_URL}/auth/google/login`;
  }

  return (
    <button
      onClick={handleLogin}
      className="rounded-lg border px-4 py-2"
    >
      Continue with Google
    </button>
  );
}