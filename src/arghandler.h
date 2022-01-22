#ifndef showArghandlerH
#define showArghandlerH

typedef struct {
	char *name;
	char *abbreviation;
	char *description;
	char *value;
} ArgOption;

typedef struct {
	int enum_val;
	char *name;
} EnumConvertInfo;

char* get_argument_values(int argc, char **argv, ArgOption options[], int option_count);
void print_help(ArgOption options[], int option_count);
int in_to_enum(char* input, EnumConvertInfo conversion_table[], int table_size);

#endif
