import { Activity, Dumbbell, Utensils } from 'lucide-react';
import FeatureCard from './FeatureCard';

const features = [
  {
    icon: Dumbbell,
    title: 'Entrenamiento sin material',
    description: 'Rutinas adaptadas a tu espacio y nivel.',
  },
  {
    icon: Utensils,
    title: 'Nutrición personalizada',
    description: 'Planes de comida ajustados a tus objetivos.',
  },
  {
    icon: Activity,
    title: 'Seguimiento dinámico',
    description: 'Ajustes automáticos con tus progresos.',
  },
];

export default function Features() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-20">
      <h2 className="mb-12 text-center text-3xl font-bold">Características</h2>
      <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <FeatureCard key={f.title} {...f} />
        ))}
      </div>
    </section>
  );
}
