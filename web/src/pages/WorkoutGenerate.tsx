import GenerateFromAI from '../features/routines/GenerateFromAI';
import Card from '../components/ui/card';
import PageHeader from '../components/layout/PageHeader';

export default function WorkoutGeneratePage() {
  return (
    <div className="mx-auto max-w-3xl p-4 space-y-4">
      <PageHeader>
        <h1 className="text-xl font-semibold">Generar rutina con IA</h1>
        <p className="text-sm opacity-90">Crea una rutina personalizada en base a tus preferencias</p>
      </PageHeader>
      <Card>
        <GenerateFromAI />
      </Card>
    </div>
  );
}
