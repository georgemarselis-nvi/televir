#!/usr/bin/env python3
"""
Accession Database CLI for TELE-Vir.

Usage:
    python accession_db_cli.py summary
    python accession_db_cli.py list [--type protein|nuc|all]
    python accession_db_cli.py search <accession> [--dbs <name>] [--limit N]
    python accession_db_cli.py coverage [--missing]
    python accession_db_cli.py export --dbs <name> --output <file>
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


class AccessionDBCLI:
    def __init__(self, install_home=None):
        self.install_home = install_home or os.environ.get('INSTALL_HOME', '/opt/televir')
        self.metadir = os.path.join(self.install_home, 'metadata')
        
        self.protein_db = os.path.join(self.metadir, 'protein_accessions.db')
        self.nucleotide_db = os.path.join(self.metadir, 'nucleotide_accessions.db')
    
    def _get_db_path(self, db_type):
        if db_type == 'protein':
            return self.protein_db
        elif db_type == 'nuc':
            return self.nucleotide_db
        return None
    
    def _query_db(self, db_path, query, params=None):
        if not os.path.exists(db_path):
            return None
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    
    def summary(self):
        """Show overall summary statistics."""
        print("\n=== Accession Database Summary ===\n")
        
        total_protein = 0
        total_nuc = 0
        protein_with_taxid = 0
        nuc_with_taxid = 0
        
        if os.path.exists(self.protein_db):
            conn = sqlite3.connect(self.protein_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM protein_accessions")
            total_protein = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM protein_accessions WHERE taxid IS NOT NULL")
            protein_with_taxid = cursor.fetchone()[0]
            
            try:
                cursor.execute("SELECT SUM(pgsize) FROM pragma_page_size()")
                page_size = cursor.fetchone()[0] or 4096
            except sqlite3.OperationalError:
                page_size = 4096
            
            try:
                cursor.execute("SELECT SUM(pages) FROM pragma_page_count()")
                pages = cursor.fetchone()[0] or 0
            except sqlite3.OperationalError:
                try:
                    cursor.execute("SELECT SUM(page_count) FROM pragma_page_count()")
                    pages = cursor.fetchone()[0] or 0
                except:
                    pages = 0
            
            protein_size = (pages * page_size / (1024 * 1024)) if pages > 0 else (os.path.getsize(self.protein_db) / (1024 * 1024) if os.path.exists(self.protein_db) else 0)
            conn.close()
        else:
            protein_size = 0
        
        if os.path.exists(self.nucleotide_db):
            conn = sqlite3.connect(self.nucleotide_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nucleotide_accessions")
            total_nuc = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM nucleotide_accessions WHERE taxid IS NOT NULL")
            nuc_with_taxid = cursor.fetchone()[0]
            
            try:
                cursor.execute("SELECT SUM(pgsize) FROM pragma_page_size()")
                page_size = cursor.fetchone()[0] or 4096
            except sqlite3.OperationalError:
                page_size = 4096
            
            try:
                cursor.execute("SELECT SUM(pages) FROM pragma_page_count()")
                pages = cursor.fetchone()[0] or 0
            except sqlite3.OperationalError:
                try:
                    cursor.execute("SELECT SUM(page_count) FROM pragma_page_count()")
                    pages = cursor.fetchone()[0] or 0
                except:
                    pages = 0
            
            nuc_size = (pages * page_size / (1024 * 1024)) if pages > 0 else (os.path.getsize(self.nucleotide_db) / (1024 * 1024) if os.path.exists(self.nucleotide_db) else 0)
            conn.close()
        else:
            nuc_size = 0
        
        protein_pct = (protein_with_taxid / total_protein * 100) if total_protein > 0 else 0
        nuc_pct = (nuc_with_taxid / total_nuc * 100) if total_nuc > 0 else 0
        
        print(f"Protein Database: {self.protein_db}")
        print(f"  - Records:       {total_protein:,}")
        print(f"  - With Taxid:   {protein_with_taxid:,} ({protein_pct:.1f}%)")
        print(f"  - Size:         {protein_size:.1f} MB")
        
        print(f"\nNucleotide Database: {self.nucleotide_db}")
        print(f"  - Records:       {total_nuc:,}")
        print(f"  - With Taxid:   {nuc_with_taxid:,} ({nuc_pct:.1f}%)")
        print(f"  - Size:         {nuc_size:.1f} MB")
        
        print(f"\nTotal Accessions: {total_protein + total_nuc:,}")
        print(f"Total with Taxid: {protein_with_taxid + nuc_with_taxid:,}")
    
    def list_dbs(self, db_type='all'):
        """List databases with statistics."""
        results = []
        
        if db_type in ('all', 'protein'):
            if os.path.exists(self.protein_db):
                conn = sqlite3.connect(self.protein_db)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dbs, COUNT(*) as total,
                           SUM(CASE WHEN taxid IS NOT NULL THEN 1 ELSE 0 END) as with_taxid
                    FROM protein_accessions
                    GROUP BY dbs
                """)
                for row in cursor.fetchall():
                    dbs, total, with_taxid = row
                    pct = (with_taxid / total * 100) if total > 0 else 0
                    results.append(['protein', dbs, total, with_taxid, f'{pct:.1f}%'])
                conn.close()
        
        if db_type in ('all', 'nuc'):
            if os.path.exists(self.nucleotide_db):
                conn = sqlite3.connect(self.nucleotide_db)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dbs, COUNT(*) as total,
                           SUM(CASE WHEN taxid IS NOT NULL THEN 1 ELSE 0 END) as with_taxid
                    FROM nucleotide_accessions
                    GROUP BY dbs
                """)
                for row in cursor.fetchall():
                    dbs, total, with_taxid = row
                    pct = (with_taxid / total * 100) if total > 0 else 0
                    results.append(['nuc', dbs, total, with_taxid, f'{pct:.1f}%'])
                conn.close()
        
        if HAS_TABULATE:
            print(tabulate(results, headers=['Type', 'Database', 'Total', 'With Taxid', 'Coverage'], tablefmt='grid'))
        else:
            print("\n{:<10} {:<20} {:>10} {:>10} {:>10}".format('Type', 'Database', 'Total', 'With Taxid', 'Coverage'))
            print("-" * 65)
            for row in results:
                print("{:<10} {:<20} {:>10,} {:>10,} {:>10}".format(*row))
    
    def search(self, accession=None, dbs=None, limit=50):
        """Search for accessions."""
        results = []
        
        if dbs:
            # Search specific database
            if os.path.exists(self.protein_db):
                conn = sqlite3.connect(self.protein_db)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dbs, acc, description, taxid, file
                    FROM protein_accessions
                    WHERE acc LIKE ? OR (dbs = ? AND 1=1)
                    LIMIT ?
                """, (f'%{accession}%', dbs, limit) if accession else (f'%{dbs}%', dbs, limit))
                for row in cursor.fetchall():
                    results.append(('protein', row[1], row[2], row[3], row[4]))
                conn.close()
            
            if os.path.exists(self.nucleotide_db):
                conn = sqlite3.connect(self.nucleotide_db)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dbs, acc, acc_in_file, taxid, file
                    FROM nucleotide_accessions
                    WHERE acc LIKE ? OR (dbs = ? AND 1=1)
                    LIMIT ?
                """, (f'%{accession}%', dbs, limit) if accession else (f'%{dbs}%', dbs, limit))
                for row in cursor.fetchall():
                    results.append(('nuc', row[1], row[3], row[4], row[5] if len(row) > 4 else ''))
                conn.close()
        else:
            # Search both databases
            if os.path.exists(self.protein_db):
                conn = sqlite3.connect(self.protein_db)
                cursor = conn.cursor()
                if accession:
                    cursor.execute("""
                        SELECT dbs, acc, description, taxid, file
                        FROM protein_accessions
                        WHERE acc LIKE ?
                        LIMIT ?
                    """, (f'%{accession}%', limit))
                else:
                    cursor.execute("""
                        SELECT dbs, acc, description, taxid, file
                        FROM protein_accessions
                        LIMIT ?
                    """, (limit,))
                for row in cursor.fetchall():
                    results.append(('protein', row[1], row[2], row[3], row[4]))
                conn.close()
            
            if os.path.exists(self.nucleotide_db):
                conn = sqlite3.connect(self.nucleotide_db)
                cursor = conn.cursor()
                if accession:
                    cursor.execute("""
                        SELECT dbs, acc, acc_in_file, taxid, file
                        FROM nucleotide_accessions
                        WHERE acc LIKE ?
                        LIMIT ?
                    """, (f'%{accession}%', limit))
                else:
                    cursor.execute("""
                        SELECT dbs, acc, acc_in_file, taxid, file
                        FROM nucleotide_accessions
                        LIMIT ?
                    """, (limit,))
                for row in cursor.fetchall():
                    results.append(('nuc', row[1], row[3], row[4], row[5] if len(row) > 4 else ''))
                conn.close()
        
        if not results:
            print("No results found.")
            return
        
        print(f"\nShowing {len(results)} results:\n")
        if HAS_TABULATE:
            print(tabulate(results, headers=['Type', 'Accession', 'Description/AccInFile', 'TaxID', 'File'], tablefmt='grid'))
        else:
            print("{:<10} {:<25} {:<40} {:>10} {:<30}".format('Type', 'Accession', 'Description/AccInFile', 'TaxID', 'File'))
            print("-" * 120)
            for row in results:
                desc = str(row[2])[:40] if row[2] else ''
                taxid = str(row[3]) if row[3] else ''
                print("{:<10} {:<25} {:<40} {:>10} {:<30}".format(row[0], row[1], desc, taxid, str(row[4])[:30]))
    
    def coverage(self, missing_only=False):
        """Show taxid coverage report."""
        results = []
        
        if os.path.exists(self.protein_db):
            conn = sqlite3.connect(self.protein_db)
            cursor = conn.cursor()
            if missing_only:
                cursor.execute("""
                    SELECT dbs, COUNT(*) as missing
                    FROM protein_accessions
                    WHERE taxid IS NULL
                    GROUP BY dbs
                    ORDER BY missing DESC
                """)
            else:
                cursor.execute("""
                    SELECT dbs, COUNT(*) as total,
                           SUM(CASE WHEN taxid IS NOT NULL THEN 1 ELSE 0 END) as with_taxid
                    FROM protein_accessions
                    GROUP BY dbs
                """)
            for row in cursor.fetchall():
                if missing_only:
                    results.append(['protein', row[0], row[1], 0, 0])
                else:
                    pct = (row[2] / row[1] * 100) if row[1] > 0 else 0
                    results.append(['protein', row[0], row[1], row[2], f'{pct:.1f}%'])
            conn.close()
        
        if os.path.exists(self.nucleotide_db):
            conn = sqlite3.connect(self.nucleotide_db)
            cursor = conn.cursor()
            if missing_only:
                cursor.execute("""
                    SELECT dbs, COUNT(*) as missing
                    FROM nucleotide_accessions
                    WHERE taxid IS NULL
                    GROUP BY dbs
                    ORDER BY missing DESC
                """)
            else:
                cursor.execute("""
                    SELECT dbs, COUNT(*) as total,
                           SUM(CASE WHEN taxid IS NOT NULL THEN 1 ELSE 0 END) as with_taxid
                    FROM nucleotide_accessions
                    GROUP BY dbs
                """)
            for row in cursor.fetchall():
                if missing_only:
                    results.append(['nuc', row[0], row[1], 0, 0])
                else:
                    pct = (row[2] / row[1] * 100) if row[1] > 0 else 0
                    results.append(['nuc', row[0], row[1], row[2], f'{pct:.1f}%'])
            conn.close()
        
        if missing_only:
            total_missing = sum(r[2] for r in results)
            print(f"\n=== Accessions Missing Taxid (Total: {total_missing:,}) ===\n")
            if HAS_TABULATE:
                print(tabulate(results, headers=['Type', 'Database', 'Missing Count'], tablefmt='grid'))
            else:
                print("{:<10} {:<20} {:>15}".format('Type', 'Database', 'Missing Count'))
                print("-" * 50)
                for row in results:
                    print("{:<10} {:<20} {:>15,}".format(row[0], row[1], row[2]))
        else:
            print("\n=== Taxid Coverage Report ===\n")
            if HAS_TABULATE:
                print(tabulate(results, headers=['Type', 'Database', 'Total', 'With Taxid', 'Coverage'], tablefmt='grid'))
            else:
                print("{:<10} {:<20} {:>10} {:>12} {:>10}".format('Type', 'Database', 'Total', 'With Taxid', 'Coverage'))
                print("-" * 70)
                for row in results:
                    print("{:<10} {:<20} {:>10,} {:>12,} {:>10}".format(row[0], row[1], row[2], row[3], row[4]))
    
    def export(self, dbs=None, output=None):
        """Export accession data to file."""
        if not output:
            print("Error: --output required", file=sys.stderr)
            sys.exit(1)
        
        total_exported = 0
        
        if os.path.exists(self.protein_db):
            conn = sqlite3.connect(self.protein_db)
            cursor = conn.cursor()
            
            if dbs:
                cursor.execute("""
                    SELECT acc, taxid FROM protein_accessions
                    WHERE dbs = ? AND taxid IS NOT NULL
                """, (dbs,))
            else:
                cursor.execute("""
                    SELECT acc, taxid FROM protein_accessions
                    WHERE taxid IS NOT NULL
                """)
            
            with open(output, 'w') as f:
                f.write("accession\ttaxid\n")
                for row in cursor.fetchall():
                    f.write(f"{row[0]}\t{row[1]}\n")
                    total_exported += 1
            conn.close()
        
        if os.path.exists(self.nucleotide_db):
            conn = sqlite3.connect(self.nucleotide_db)
            cursor = conn.cursor()
            
            mode = 'a' if total_exported > 0 else 'w'
            with open(output, mode) as f:
                if total_exported == 0:
                    f.write("accession\ttaxid\n")
                cursor.execute("""
                    SELECT acc, taxid FROM nucleotide_accessions
                    WHERE taxid IS NOT NULL
                """)
                for row in cursor.fetchall():
                    f.write(f"{row[0]}\t{row[1]}\n")
                    total_exported += 1
            conn.close()
        
        print(f"Exported {total_exported:,} records to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="TELE-Vir Accession Database CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--home', 
        default=None,
        help='Installation home directory (default: INSTALL_HOME env var or /opt/televir)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # summary command
    subparsers.add_parser('summary', help='Show overall summary statistics')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List databases with statistics')
    list_parser.add_argument(
        '--type', 
        choices=['protein', 'nuc', 'all'], 
        default='all',
        help='Database type to list (default: all)'
    )
    
    # search command
    search_parser = subparsers.add_parser('search', help='Search accessions')
    search_parser.add_argument('accession', nargs='?', help='Accession to search for')
    search_parser.add_argument('--dbs', help='Filter by database name')
    search_parser.add_argument('--limit', type=int, default=50, help='Limit results (default: 50)')
    
    # coverage command
    coverage_parser = subparsers.add_parser('coverage', help='Show taxid coverage report')
    coverage_parser.add_argument('--missing', action='store_true', help='Show only databases with missing taxids')
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export accession data to file')
    export_parser.add_argument('--dbs', help='Filter by database name')
    export_parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = AccessionDBCLI(install_home=args.home)
    
    if args.command == 'summary':
        cli.summary()
    elif args.command == 'list':
        cli.list_dbs(args.type)
    elif args.command == 'search':
        cli.search(args.accession, args.dbs, args.limit)
    elif args.command == 'coverage':
        cli.coverage(args.missing)
    elif args.command == 'export':
        cli.export(args.dbs, args.output)


if __name__ == '__main__':
    main()