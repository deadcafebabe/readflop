from sys import argv
import argparse

def find_file(filename, dir_table, buffer, data_addr, bdb):
    entry = dict()

    for i in dir_table:
        if filename in i.values():
            entry = i
            break

    if not entry:
        raise FileNotFoundError
    
    file_addr = data_addr + (entry['cluster_num'] - 2) * bdb['sectors_per_cluster'] * bdb['bytes_per_sector']
    
    with open(filename, 'wb') as f:
        f.write(buffer[file_addr:file_addr + entry['file_size']])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('-e', '--extract', type=str, nargs=1, help='Extracts the file specified')
    args = ap.parse_args()

    bdb = dict()

    try:
        with open(args.image, "rb") as f:
            buffer = f.read()
    except FileNotFoundError:
        print(f"Error: Couldn't find disk image {args.image}")
        return None
    
    bdb['bytes_per_sector']      = int.from_bytes(buffer[0xB: 0xB + 2], 'little')
    bdb['sectors_per_cluster']   = int.from_bytes(buffer[0xD: 0xD + 1], 'little')
    bdb['reserved_sectors']      = int.from_bytes(buffer[0xE: 0xE + 2], 'little')
    bdb['fat_count']             = int.from_bytes(buffer[0x10: 0x10 + 1], 'little')
    bdb['dir_entries_count']     = int.from_bytes(buffer[0x11: 0x11 + 2], 'little')
    bdb['sectors_per_fat']       = int.from_bytes(buffer[0x16: 0x16 + 2], 'little')

    fat_addr = bdb['reserved_sectors'] * bdb['bytes_per_sector']
    root_addr = fat_addr + bdb['fat_count'] * bdb['sectors_per_fat'] * bdb['bytes_per_sector']
    data_addr = root_addr + bdb['dir_entries_count'] * 32

    filename = buffer[root_addr: root_addr + 8].rstrip()
    i = root_addr
    dir_table = []
    
    while filename[0] != 0:
        dir_entry = dict()
        fn = filename.decode('utf-8')
        ext = buffer[i + 8:i + 8 + 3].rstrip().decode('utf-8')

        full_fn = fn + '.' + ext if len(ext) > 0 else fn

        dir_entry['filename']    = full_fn
        dir_entry['attribute']   = int.from_bytes(buffer[i + 0xB:i + 0xB + 1], 'little')
        dir_entry['cluster_num'] = int.from_bytes(buffer[i + 0x1A:i + 0x1A + 2], 'little')
        dir_entry['file_size']   = int.from_bytes(buffer[i + 0x1C:i + 0x1C + 4], 'little')
        dir_table.append(dir_entry)
        i += 32
        filename = buffer[i:i + 8].rstrip()

    if args.extract is not None:
        try:
            find_file(args.extract[0], dir_table, buffer, data_addr, bdb)
        except FileNotFoundError:
            print('Error: No such file or directory')
    else:
        for i in dir_table:
            print(i['filename'])

if __name__ == '__main__':
    main()