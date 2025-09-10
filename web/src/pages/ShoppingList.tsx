import ShoppingList from '../features/nutrition/ShoppingList';
import Card from '../components/ui/card';
import PageHeader from '../components/layout/PageHeader';

export default function ShoppingListPage() {
  return (
    <div className="mx-auto max-w-4xl p-4 space-y-4">
      <PageHeader>
        <h1 className="text-xl font-semibold">Lista de la compra</h1>
        <p className="text-sm opacity-90">Agrupada por tipo de alimento. Copia o descarga en CSV.</p>
      </PageHeader>
      <Card>
        <ShoppingList />
      </Card>
    </div>
  );
}
