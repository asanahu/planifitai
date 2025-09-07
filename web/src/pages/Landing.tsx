import { Suspense, lazy } from 'react';
import Hero from '../components/marketing/Hero';
import FinalCTA from '../components/marketing/FinalCTA';
import MainNavbar from '../components/layout/MainNavbar';
import SiteFooter from '../components/layout/SiteFooter';

const Features = lazy(() => import('../components/marketing/Features'));
const HowItWorks = lazy(() => import('../components/marketing/HowItWorks'));
const Testimonials = lazy(() => import('../components/marketing/Testimonials'));

export default function Landing() {
  return (
    <>
      <MainNavbar />
      <main>
        <Hero />
        <Suspense fallback={<div />}>
          <Features />
          <HowItWorks />
          <Testimonials />
        </Suspense>
        <FinalCTA />
      </main>
      <SiteFooter />
    </>
  );
}
