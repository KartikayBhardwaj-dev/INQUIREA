import GoogleLoginButton from "@/features/auth/components/GoogleLoginButton";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold">
            Welcome to INQUIREA
          </h1>

          <p className="mt-2 text-gray-500">
            Sign in to continue
          </p>
        </div>

        <GoogleLoginButton />
      </div>
    </main>
  );
}