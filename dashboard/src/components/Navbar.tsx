import React from 'react';
import Link from 'next/link';

const Navbar: React.FC = () => {
    return (
<nav className="bg-gray-800 text-white p-4">
      <ul className="flex space-x-4">
        <li>
          <Link href="/" className="hover:bg-gray-700 p-2 rounded">👩‍💼</Link>
        </li>
        <li>
          <Link href="/dashboard" className="hover:bg-gray-700 p-2 rounded">Dashboard</Link>
        </li>
        <li>
          <Link href="/pipelines" className="hover:bg-gray-700 p-2 rounded">Pipelines</Link>
        </li>
      </ul>
    </nav>
    );
}

export default Navbar;
