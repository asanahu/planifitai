import Card from '../ui/card';
import { motion, useReducedMotion } from 'framer-motion';

const testimonials = [
  {
    name: 'Ana',
    avatar: 'https://i.pravatar.cc/80?img=1',
    text: 'Con PlanifitAI me mantengo constante y veo resultados reales.',
    stat: '-5kg en 2 meses',
  },
  {
    name: 'Luis',
    avatar: 'https://i.pravatar.cc/80?img=2',
    text: 'La nutrición personalizada simplificó mi día a día.',
    stat: '+3kg de músculo',
  },
  {
    name: 'María',
    avatar: 'https://i.pravatar.cc/80?img=3',
    text: 'El seguimiento dinámico ajusta mi plan cuando lo necesito.',
    stat: 'Mejor tono y energía',
  },
];

export default function Testimonials() {
  const prefersReducedMotion = useReducedMotion();
  return (
    <section className="mx-auto max-w-7xl px-4 py-20">
      <h2 className="mb-12 text-center text-3xl font-bold">Testimonios</h2>
      <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
        {testimonials.map((t) => (
          <motion.div
            key={t.name}
            initial={prefersReducedMotion ? undefined : { opacity: 0, y: 20 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.4 }}
          >
            <Card className="text-center">
              <img src={t.avatar} alt="avatar" className="mx-auto mb-4 h-16 w-16 rounded-full" loading="lazy" />
              <p className="mb-4 text-sm">“{t.text}”</p>
              <div className="font-semibold">{t.name}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">{t.stat}</div>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
