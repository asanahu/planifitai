import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../features/auth/useAuthStore';

export function useAuth() {
  const navigate = useNavigate();
  const { user, logout: storeLogout } = useAuthStore();
  const logout = async () => {
    storeLogout();
    navigate('/login');
  };
  return { user, logout };
}
