import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'Tumor Dynamics Lab',description:'Local lineage composition research workbench'};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>;}
