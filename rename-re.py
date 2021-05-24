import os, sys, re

def test(filename, src_pattern, dist_pattern):
    match = src_pattern.match(filename)
    if match:
        dist_name = dist_pattern
        for i, prop in enumerate(match.groups(), start=1):
            dist_name = dist_name.replace('$' + str(i), prop)
        return dist_name
    else:
        return None

def bulk_test(path, src_pattern, dist_pattern):
    filelist = os.listdir(path)
    count = 0
    for filename in filelist:
        fullpath = os.path.join(path, filename)
        if os.path.isfile(fullpath):
            dist_name = test(filename, src_pattern, dist_pattern)
            if dist_name is not None:
                print('"' + filename + '" will be renamed "' + dist_name + '".')
                count += 1
            else:
                print('"' + filename + '" cannot match the pattern.')
    print(str(count) + ' files will be renamed.')

def rename(path, filename, src_pattern, dist_pattern):
    src_fullpath = os.path.join(path, filename)
    match = src_pattern.match(filename)
    if match:
        dist_name = dist_pattern
        for i, prop in enumerate(match.groups(), start=1):
            dist_name = dist_name.replace('$' + str(i), prop)
        dist_fullpath = os.path.join(path, dist_name)
        os.rename(src_fullpath, dist_fullpath)


def bulk_rename(path, src_pattern, dist_pattern):
    filelist = os.listdir(path)
    count = 0
    for filename in filelist:
        fullpath = os.path.join(path, filename)
        if os.path.isfile(fullpath):
            rename(path, filename, src_pattern, dist_pattern)
            count += 1
    print('OK: ' + str(count) + ' files affected.')

if __name__ == '__main__':
    path = input('Path: ')
    src_pattern = input('Source file pattern (regex): ')
    dist_pattern = input('Dist file pattern (use $n): ')

    src_pattern = re.compile(src_pattern)
    bulk_test(path, src_pattern, dist_pattern)
    if input('Rename those files? (y/n):') == 'y':
        bulk_rename(path, src_pattern, dist_pattern)
