#include <stdio.h>
#include <string.h>
#include "arghandler.h"

char* get_argument_values(int argc, char **argv, ArgOption *options, int option_count) {
	int arg_index = 1, option_index = 0;
	_Bool option_found = 0;
	char* file_path = "";
	while (arg_index < argc) {
		option_index = 0;
		option_found = 0;
		while (option_index < option_count && !option_found) {
			if(strcmp(argv[arg_index], options[option_index].name)  == 0||
			   strcmp(argv[arg_index], options[option_index].abbreviation) == 0) {
				arg_index++;
				if (arg_index < argc)
					options[option_index].value = argv[arg_index];
				option_found = 1;
			}
			option_index++;
		}
		if(!option_found) {
			file_path = argv[arg_index];
		}
		arg_index++;
	}
	return file_path;
}

void print_help(ArgOption *options, int option_count) {
	printf("show - A Shader background for your desktop\n\n");
	printf("Usage: show <path> [options]\n");
	printf("Options:\n");
	for (int i = 0; i < option_count; i++) {
		printf("\t%-4s %-15s %s\n", options[i].abbreviation, options[i].name, options[i].description);
	}
}

int in_to_enum(char* input, EnumConvertInfo conversion_table[], int table_size) {
	for (int i = 0; i < table_size; i++)
		if(strcmp(input, conversion_table[i].name) == 0)
			return conversion_table[i].enum_val;
	return -1;
}
