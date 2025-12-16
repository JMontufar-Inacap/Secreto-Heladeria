import { Card, CardContent } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const stats = [
  { title: "Unidades Vendidas", value: 1248, change: +8.4 },
  { title: "Órdenes Realizadas", value: 312, change: +4.1 },
  { title: "Dinero Recibido", value: "$2.450.000", change: -1.2 },
  { title: "Clientes Activos", value: 198, change: +6.9 },
];

const ganancias = [
  { mes: "Ene", total: 120000 },
  { mes: "Feb", total: 98000 },
  { mes: "Mar", total: 135000 },
  { mes: "Abr", total: 160000 },
  { mes: "May", total: 175000 },
  { mes: "Jun", total: 190000 },
  { mes: "Jul", total: 210000 },
  { mes: "Ago", total: 205000 },
  { mes: "Sep", total: 225000 },
  { mes: "Oct", total: 240000 },
  { mes: "Nov", total: 260000 },
  { mes: "Dic", total: 280000 },
];

const topProductos = [
  { nombre: "Helado Chocolate", vendidos: 420 },
  { nombre: "Helado Vainilla", vendidos: 390 },
  { nombre: "Helado Frutilla", vendidos: 355 },
];

export default function DashboardHeladeria() {
  return (
    <div className="p-6 space-y-6">
      {/* Cards superiores (última semana) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <Card key={i} className="rounded-2xl shadow-sm">
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">{s.title}</p>
              <p className="text-2xl font-semibold mt-1">{s.value}</p>
              <div className={`flex items-center text-sm mt-2 ${s.change >= 0 ? "text-green-600" : "text-red-600"}`}>
                {s.change >= 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                <span>{Math.abs(s.change)}% última semana</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Ganancias + Top productos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 rounded-2xl">
          <CardContent className="p-4">
            <h3 className="font-semibold mb-4">Ganancias últimos 12 meses</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ganancias}>
                  <XAxis dataKey="mes" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardContent className="p-4">
            <h3 className="font-semibold mb-4">Top 3 productos (último mes)</h3>
            <ul className="space-y-3">
              {topProductos.map((p, i) => (
                <li key={i} className="flex justify-between text-sm">
                  <span>{p.nombre}</span>
                  <span className="font-medium">{p.vendidos}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Órdenes 12 meses + extra */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 rounded-2xl">
          <CardContent className="p-4">
            <h3 className="font-semibold mb-2">Órdenes últimos 12 meses</h3>
            <p className="text-3xl font-bold">4.863</p>
            <p className="text-sm text-muted-foreground">+12% vs año anterior</p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardContent className="p-4">
            <h3 className="font-semibold mb-2">Resumen rápido</h3>
            <ul className="text-sm space-y-2">
              <li>Ticket promedio: <strong>$8.450</strong></li>
              <li>Producto más rentable: <strong>Chocolate</strong></li>
              <li>Hora pico ventas: <strong>18:00 – 20:00</strong></li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
