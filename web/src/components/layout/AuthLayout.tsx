import type { ReactNode } from 'react';
import MainNavbar from './MainNavbar';
import SiteFooter from './SiteFooter';
import Card from '../ui/card';

interface AuthLayoutProps {
  title: string;
  subtitle?: string;
  cardTitle?: string;
  children: ReactNode;
}

export default function AuthLayout({ title, subtitle, cardTitle, children }: AuthLayoutProps) {
  return (
    <>
      <MainNavbar />
      <main>
        <section className="bg-gradient-to-br from-planifit-500 via-violet-500 to-indigo-500 py-16 text-white">
          <div className="mx-auto max-w-7xl px-4 text-center">
            <h1 className="text-3xl font-bold md:text-4xl">{title}</h1>
            {subtitle && <p className="mt-2 opacity-90">{subtitle}</p>}
          </div>
        </section>
        <section className="bg-gray-50 py-12 dark:bg-gray-950">
          <div className="mx-auto max-w-md px-4">
            <Card className="p-6">
              {cardTitle && (
                <h2 className="mb-4 text-center text-xl font-semibold">{cardTitle}</h2>
              )}
              {children}
            </Card>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}

