import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { authApi, type User } from '../services/api';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireEmailVerified?: boolean;
}

export default function ProtectedRoute({ children, requireEmailVerified = false }: ProtectedRouteProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await authApi.getMe();
        setUser(userData);

        if (requireEmailVerified && !userData.is_email_verified) {
          // Redirect to login with verification message
          return;
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [requireEmailVerified]);

  if (isLoading) {
    return null; // Or loading spinner
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requireEmailVerified && !user.is_email_verified) {
    return <Navigate to="/login" state={{ needVerification: true }} replace />;
  }

  return <>{children}</>;
}