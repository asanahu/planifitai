import { Link } from 'react-router-dom';
import Button from '../ui/button';

export default function FinalCTA() {
  return (
    <section className="bg-gradient-to-r from-planifit-600 to-violet-600 py-16 text-center text-white">
      <h2 className="mb-4 text-3xl font-bold">¿Listo para comenzar?</h2>
      <p className="mb-8">Crea tu plan ahora mismo.</p>
      <Button asChild>
        <Link to="/register">Comenzar ahora</Link>
      </Button>
    </section>
  );
}
