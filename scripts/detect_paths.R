# 경로 자동 감지 유틸리티 (R 버전)
# source("scripts/detect_paths.R") 형태로 불러서 사용

library(jsonlite)

get_workspace_root <- function() {
  # 1순위: 환경변수
  env_root <- Sys.getenv("AGENT_WORKSPACE_ROOT", unset = NA)
  if (!is.na(env_root) && nchar(env_root) > 0) return(normalizePath(env_root))

  # 2순위: config.local.json 탐색 (현재 디렉토리 → 상위 최대 3단계)
  search_dirs <- c(
    getwd(),
    dirname(getwd()),
    dirname(dirname(getwd()))
  )
  for (d in search_dirs) {
    local_cfg <- file.path(d, "config.local.json")
    if (file.exists(local_cfg)) return(normalizePath(d))
  }

  # 3순위: 현재 작업 디렉토리
  normalizePath(getwd())
}

load_config <- function() {
  workspace_root <- get_workspace_root()
  local_cfg_path <- file.path(workspace_root, "config.local.json")

  if (file.exists(local_cfg_path)) {
    cfg <- fromJSON(local_cfg_path)
    cfg$workspace_root <- workspace_root
    return(resolve_placeholders(cfg))
  }

  build_default_config(workspace_root)
}

build_default_config <- function(workspace_root) {
  data_root   <- file.path(workspace_root, "data")
  output_root <- file.path(workspace_root, "output")
  list(
    machine_id     = "auto-detected",
    workspace_root = workspace_root,
    data_root      = data_root,
    output_root    = output_root,
    python_path    = "python",
    r_path         = "Rscript",
    paths = list(
      raw_data         = file.path(data_root,   "raw"),
      processed_data   = file.path(data_root,   "processed"),
      analysis_output  = file.path(output_root, "analysis"),
      webapp_output    = file.path(output_root, "webapp"),
      pptx_output      = file.path(output_root, "pptx"),
      reports          = file.path(output_root, "reports")
    )
  )
}

resolve_placeholders <- function(cfg) {
  replacements <- c(
    "\\{workspace_root\\}" = cfg$workspace_root %||% "",
    "\\{data_root\\}"      = cfg$data_root      %||% "",
    "\\{output_root\\}"    = cfg$output_root    %||% ""
  )
  if (!is.null(cfg$paths)) {
    cfg$paths <- lapply(cfg$paths, function(p) {
      for (pat in names(replacements)) p <- gsub(pat, replacements[[pat]], p)
      p
    })
  }
  cfg
}

ensure_directories <- function(cfg) {
  invisible(lapply(cfg$paths, function(p) {
    if (!dir.exists(p)) dir.create(p, recursive = TRUE)
  }))
}

`%||%` <- function(a, b) if (!is.null(a) && nchar(a) > 0) a else b

# 실행 시 설정 출력
if (interactive()) {
  cfg <- load_config()
  cat("머신 ID:", cfg$machine_id, "\n")
  cat("워크스페이스:", cfg$workspace_root, "\n\n경로 설정:\n")
  for (nm in names(cfg$paths)) cat(" ", nm, ":", cfg$paths[[nm]], "\n")
}
