import { useState } from "react";
import { signIn } from "next-auth/react";

export const useGoogleLogin = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      await signIn("google");
    } catch (error) {
      console.error("Login error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, handleLogin };
};
