import type { LucideIcon } from 'lucide-react';
import Card from '../ui/card';
import { motion, useReducedMotion } from 'framer-motion';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export default function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <motion.div
      initial={prefersReducedMotion ? undefined : { opacity: 0, y: 20 }}
      whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.4 }}
    >
      <Card className="text-center">
        <Icon className="mx-auto mb-4 h-10 w-10 text-planifit-600" />
        <h3 className="mb-2 font-semibold">{title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-300">{description}</p>
      </Card>
    </motion.div>
  );
}
