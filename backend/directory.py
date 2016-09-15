import fileinput
import os
import time

def getFilesObjects(directory, files = None, binary = True):
    all_files = []
    # print("needed_files: ")
    # print(files_name)
    files = getFilesAtDirectory(directory, files, add_path = True, extra = False)
    # print(files)
    try:
        for file_name in files:
            all_files.append(open(file_name, "rb" if binary else "r"))
    except Exception as e:
        print(e)

    return all_files

def getFilesAtDirectory(directory, needed_files = None, add_path = False, extra = True):
    #retorna none si no existe el directorio y [] si está vacio
    try:
        results = []
        if needed_files:
             needed_files = [l[0] for l in needed_files]
        for (dirpath, dirnames, filenames) in os.walk(directory):
            if needed_files:
                if extra:
                    results.extend(((((((dirpath + '/') if add_path else '') + nfile) if nfile in needed_files else ''), (os.path.getsize((dirpath + '/') + nfile) if nfile in needed_files else '')), time.ctime(os.path.getmtime((dirpath + '/') + nfile))) for nfile, nfile, nfile in zip(filenames, filenames, filenames))
                else:
                    results.extend((((dirpath + '/') if add_path else '') + nfile)  if nfile in needed_files else '' for nfile in filenames)
            else:
                if extra:
                    results.extend(((((dirpath + '/') if add_path else '') + nfile), os.path.getsize((dirpath + '/') + nfile), time.ctime(os.path.getmtime((dirpath + '/') + nfile))) for nfile, nfile, nfile in zip(filenames, filenames, filenames))
                else:
                    results.extend((((dirpath + '/') if add_path else '') + nfile) for nfile in filenames)
            break
        else:
            results = None
        # print("resultados: ")
        # print(results)
        if needed_files:
            results = list(filter(('').__ne__, results))
        # print(results)
    except Exception as e:
        print(e)
        results = []
    return results
