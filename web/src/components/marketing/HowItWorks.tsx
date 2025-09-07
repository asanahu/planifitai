import { Calendar, Sparkles, CheckCircle } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';

const steps = [
  {
    icon: Calendar,
    title: 'Completa tu perfil',
    description: 'Indícanos tus objetivos y preferencias.',
  },
  {
    icon: Sparkles,
    title: 'Genera tu plan',
    description: 'La IA crea entrenamiento y nutrición a medida.',
  },
  {
    icon: CheckCircle,
    title: 'Sigue y ajusta',
    description: 'Registra tu progreso y recibe ajustes automáticos.',
  },
];

export default function HowItWorks() {
  const prefersReducedMotion = useReducedMotion();
  return (
    <section className="bg-gray-50 py-20 dark:bg-gray-800" id="como-funciona">
      <h2 className="mb-12 text-center text-3xl font-bold">Cómo funciona</h2>
      <div className="mx-auto max-w-3xl space-y-8 px-4">
        {steps.map((step, i) => (
          <motion.div
            key={step.title}
            className="relative grid grid-cols-[auto,1fr] gap-4"
            initial={prefersReducedMotion ? undefined : { opacity: 0, x: -20 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.4 }}
          >
            <div className="flex flex-col items-center">
              <step.icon className="h-6 w-6 text-planifit-600" />
              {i < steps.length - 1 && (
                <div className="h-full w-px flex-1 bg-gray-300 dark:bg-gray-600" aria-hidden="true" />
              )}
            </div>
            <div>
              <h3 className="font-semibold">{step.title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">{step.description}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
