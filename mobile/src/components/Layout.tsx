import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';

export default function Layout() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: 'var(--bg)' }}>
      <Header />
      <main style={{ flex: 1, overflowY: 'auto', padding: '1rem', paddingBottom: '2rem' }}>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
