import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ABYSSEYE | Underwater Debris & Ghost Net Sonar Evidence Engine',
  description: 'AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery (SIH 2026 Problem 26057)',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-ocean-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
