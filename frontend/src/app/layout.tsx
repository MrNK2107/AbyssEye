import type { Metadata } from 'next';
import './globals.css';
import { AnalysisProvider } from '@/context/AnalysisContext';
import { AppShell } from '@/components/AppShell';

export const metadata: Metadata = {
  title: 'ABYSSEYE — Underwater Sonar Intelligence',
  description:
    'AI-assisted side-scan sonar detection, segmentation and validation for underwater surveys.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap"
        />
      </head>
      <body>
        <AnalysisProvider>
          <AppShell>{children}</AppShell>
        </AnalysisProvider>
      </body>
    </html>
  );
}
