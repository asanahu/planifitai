import { motion, useReducedMotion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Button from '../ui/button';

const variant = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

export default function Hero() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section className="bg-gradient-to-br from-planifit-500 via-violet-500 to-indigo-500 py-24 text-white">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-6 px-4 text-center">
        <motion.h1
          initial={prefersReducedMotion ? undefined : 'hidden'}
          animate={prefersReducedMotion ? undefined : 'visible'}
          variants={variant}
          transition={{ duration: 0.6 }}
          className="text-4xl font-bold md:text-6xl"
        >
          Planes inteligentes para tu salud
        </motion.h1>
        <motion.p
          initial={prefersReducedMotion ? undefined : 'hidden'}
          animate={prefersReducedMotion ? undefined : 'visible'}
          variants={variant}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="max-w-2xl text-lg"
        >
          Entrenamiento sin material, nutrición personalizada y seguimiento dinámico.
        </motion.p>
        <motion.div
          initial={prefersReducedMotion ? undefined : 'hidden'}
          animate={prefersReducedMotion ? undefined : 'visible'}
          variants={variant}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="flex flex-col gap-4 sm:flex-row"
        >
          <Button asChild>
            <Link to="/register">Comenzar ahora</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link to="#demo">Ver demo</Link>
          </Button>
        </motion.div>
      </div>
    </section>
  );
}

