import './globals.css';
import Providers from './providers'; // 👈 new file
import ClientLayout from '../components/ClientLayout'; // Import ClientLayout

export const metadata = {
  title: 'SOTA Papers',
  description: 'Explore top research papers',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-100 antialiased">
        <Providers>
          <div className="flex min-h-screen">
            <ClientLayout>{children}</ClientLayout>
          </div>
        </Providers>
      </body>
    </html>
  );
}
