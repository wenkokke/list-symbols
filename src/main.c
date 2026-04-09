#include <clang-c/Index.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

/// Safe __has_include.
#if defined(__has_include)
#define HAS_INCLUDE __has_include
#else
#define HAS_INCLUDE_STUB(include) 0
#define HAS_INCLUDE HAS_INCLUDE_STUB
#endif

/// File System Functions.
#if HAS_INCLUDE(<unistd.h>)
#include <unistd.h>
#endif

/// @brief Print the mangled names of all functions and variables declared in
/// the source file.
static void print_decl(const char *source_filename,
                       const char *const *command_line_args);

/// @brief Check if the file exists and is readable.
static bool source_filename_ok(const char *const source_filename);

/// @brief The main function.
int main(const int argc, const char *const argv[argc]) {
  for (int i = 1; i < argc; ++i) {
    const char *source_filename = argv[i];
    if (source_filename_ok(source_filename)) {
      print_decl(source_filename, NULL);
    }
    else {
      exit(1);
    }
  }
}

static bool source_filename_ok(const char *const source_filename) {
#if HAS_INCLUDE(<unistd.h>)
  if (access(source_filename, F_OK) != 0) {
    fprintf(stderr, "Error: cannot find file '%s'.\n", source_filename);
    return false;
  }
  if (access(source_filename, R_OK) != 0) {
    fprintf(stderr, "Error: cannot read file '%s'.\n", source_filename);
    return false;
  }
#endif
  return true;
}

/// @brief AST visitor function for use in `print_decl`.
static enum CXChildVisitResult
print_decl_children(CXCursor cursor, CXCursor parent, CXClientData client_data);

static void print_decl(const char *const source_filename,
                       const char *const *const command_line_args) {
  const CXIndex index = clang_createIndex(0, 0); // Create index
  const CXTranslationUnit unit =
      clang_parseTranslationUnit(index, source_filename, command_line_args, 0,
                                 NULL, 0, CXTranslationUnit_None);
  if (unit == NULL) {
    fprintf(stderr, "Error: cannot parse file '%s'.\n", source_filename);
    return;
  }
  CXCursor cursor = clang_getTranslationUnitCursor(unit);
  clang_visitChildren(cursor, print_decl_children, NULL);
}

static enum CXChildVisitResult
print_decl_children(const CXCursor cursor, const CXCursor parent,
                    const CXClientData client_data) {
  switch (clang_getCursorKind(cursor)) {
  case CXCursor_FunctionDecl:
    break;
  case CXCursor_VarDecl:
    break;
  default:
    return CXChildVisit_Recurse;
  }
  CXString current_display_name = clang_Cursor_getMangling(cursor);
  printf("%s\n", clang_getCString(current_display_name));
  clang_disposeString(current_display_name);
  return CXChildVisit_Continue;
}
