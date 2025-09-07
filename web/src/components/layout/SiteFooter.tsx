import { Link } from 'react-router-dom';

export default function SiteFooter() {
  return (
    <footer className="border-t bg-white py-10 text-sm dark:bg-gray-900" aria-label="Pie de página">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:grid-cols-2 md:grid-cols-4">
        <div>
          <h3 className="mb-2 font-semibold">Producto</h3>
          <ul className="space-y-1">
            <li><Link to="/" className="hover:underline">Inicio</Link></li>
            <li><Link to="/login" className="hover:underline">Login</Link></li>
            <li><Link to="/register" className="hover:underline">Registro</Link></li>
          </ul>
        </div>
        <div>
          <h3 className="mb-2 font-semibold">Recursos</h3>
          <ul className="space-y-1">
            <li><a href="#" className="hover:underline">Blog</a></li>
            <li><a href="#" className="hover:underline">Ayuda</a></li>
          </ul>
        </div>
        <div>
          <h3 className="mb-2 font-semibold">Empresa</h3>
          <ul className="space-y-1">
            <li><a href="#" className="hover:underline">Acerca de</a></li>
            <li><a href="#" className="hover:underline">Contacto</a></li>
          </ul>
        </div>
        <div>
          <h3 className="mb-2 font-semibold">Legal</h3>
          <ul className="space-y-1">
            <li><a href="#" className="hover:underline">Privacidad</a></li>
            <li><a href="#" className="hover:underline">Términos</a></li>
          </ul>
        </div>
      </div>
      <div className="mt-8 text-center text-xs text-gray-500">© {new Date().getFullYear()} PlanifitAI</div>
    </footer>
  );
}

