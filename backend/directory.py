import fileinput
import os

def getFilesObjects(directory, files = None, binary = True):
    all_files = []
    files = getFilesAtDirectory(directory, add_path = True, size = False) if files is None else files
    print(files)
    try:
        for file_name in files:
            all_files.append(open(file_name, "rb" if binary else "r"))
    except Exception as e:
        print(e)

    return all_files

def getFilesAtDirectory(directory, add_path = False, size = True):
    #retorna none si no existe el directorio y [] si está vacio
    try:
        results = []
        for (dirpath, dirnames, filenames) in os.walk(directory):
            if size:
                results.extend(((((dirpath + '/') if add_path else '') + nfile), os.path.getsize((dirpath + '/') + nfile)) for nfile, nfile in zip(filenames, filenames))
            else:
                results.extend((((dirpath + '/') if add_path else '') + nfile) for nfile in filenames)
            break
        else:
            results = None
    except Exception as e:
        print(e)
        results = []
    return results
