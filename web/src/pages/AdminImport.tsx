import Card from '../components/ui/card';
import PageHeader from '../components/layout/PageHeader';
import { useState } from 'react';
import { importWger, importFreeDB } from '../api/admin';
import Overlay from '../components/ui/Overlay';

export default function AdminImportPage() {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const run = async (fn: () => Promise<any>) => {
    setBusy(true); setMsg(null);
    try {
      const r = await fn();
      setMsg(`Importados: ${r.imported ?? r?.data?.imported ?? '?'}`);
    } catch (e: any) {
      setMsg(e?.message || 'Error');
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="mx-auto max-w-3xl p-4 space-y-4">
      <PageHeader>
        <h1 className="text-xl font-semibold">Admin · Importar ejercicios</h1>
        <p className="text-sm opacity-90">Necesita cabecera X-Admin-Secret</p>
      </PageHeader>
      <Card>
        <div className="space-y-3">
          <div className="flex gap-2 flex-wrap">
            <button className="btn" disabled={busy} onClick={() => run(() => importWger('es'))}>Importar Wger (es)</button>
            <button className="btn" disabled={busy} onClick={() => run(() => importFreeDB(undefined, undefined, false))}>Importar Free Exercise DB (ES)</button>
          </div>
          {msg && <div className="text-sm opacity-80">{msg}</div>}
        </div>
        {busy && <Overlay>Importando…</Overlay>}
      </Card>
    </div>
  );
}
