import MealsToday from '../features/nutrition/MealsToday';
import Card from '../components/ui/card';
import PageHeader from '../components/layout/PageHeader';
import { Link } from 'react-router-dom';
import { ArrowLeft, Calendar, Utensils } from 'lucide-react';
import { useState } from 'react';

export default function NutritionTodayPage() {
  const [actualDayName, setActualDayName] = useState('hoy');
  
  const handleDateChange = (dayName: string) => {
    setActualDayName(dayName);
  };
  
  return (
    <div className="mx-auto max-w-4xl space-y-4 p-4">
      <PageHeader className="animate-fade-in">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <Link 
              to="/nutrition/plan" 
              className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2 text-sm font-medium text-white/90 hover:bg-white/20 hover:text-white transition-all duration-200"
            >
              <ArrowLeft className="h-4 w-4" />
              Volver al plan semanal
            </Link>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Utensils className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Editar comidas del {actualDayName}</h1>
                <p className="text-sm text-white/80">Registra lo que has comido {actualDayName === 'hoy' ? 'hoy' : `el ${actualDayName}`}</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2 text-sm">
              <Calendar className="h-4 w-4 text-white/80" />
              <span className="text-white/90">{actualDayName}</span>
            </div>
          </div>
        </div>
      </PageHeader>
      
      <Card>
        <MealsToday onDateChange={handleDateChange} />
      </Card>
    </div>
  );
}
