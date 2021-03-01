import yaml

with open('settings/settings.yaml') as file:
    test_list = yaml.safe_load(file)


    for piece, piece_info in test_list['pieces'].items():
        print(piece)
        for info in piece_info:
            print(info, ":", piece_info[info])