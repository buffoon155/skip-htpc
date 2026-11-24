#!/bin/bash
# Living-room launcher: ./launch.sh kodi|netflix|areena|next|status
# Google Chrome is preferred. Chromium is only the fallback.
set -euo pipefail

NETFLIX_URL_DEFAULT=https://www.netflix.com
AREENA_URL_DEFAULT=https://areena.yle.fi

script_dir() {
  cd "$(dirname "$0")" && pwd
}

config_file() {
  if [[ -n "${SKIP_HTPC_CONFIG_YAML:-}" ]]; then
    printf '%s\n' "$SKIP_HTPC_CONFIG_YAML"
    return
  fi
  local dir
  dir=$(script_dir)
  if [[ -f "${dir}/config.yaml" ]]; then
    printf '%s\n' "${dir}/config.yaml"
    return
  fi
  if [[ -f /etc/skip-htpc/config.yaml ]]; then
    printf '%s\n' /etc/skip-htpc/config.yaml
    return
  fi
  if [[ -f /usr/local/share/skip-htpc/config.yaml ]]; then
    printf '%s\n' /usr/local/share/skip-htpc/config.yaml
    return
  fi
  printf '%s\n' "${dir}/config.yaml"
}

trim() {
  local value=$1
  value=${value#"${value%%[![:space:]]*}"}
  value=${value%"${value##*[![:space:]]}"}
  value=${value//\"/}
  value=${value//\'/}
  printf '%s\n' "$value"
}

# cycle_order is a same-line list: cycle_order: [kodi, netflix, areena]
# A YAML list on the following lines is rejected.
read_cycle_order() {
  local file=$1 line inside item
  line=$(grep -E '^cycle_order:[[:space:]]*\[[^]]*\][[:space:]]*(#.*)?$' "$file" | head -n 1 || true)
  if [[ -z "$line" ]]; then
    echo "cycle_order must be a same-line list, for example [kodi, netflix, areena]" >&2
    return 1
  fi
  inside=${line#*[}
  inside=${inside%%]*}
  cycle=()
  local IFS=','
  read -r -a parts <<< "$inside"
  for item in "${parts[@]}"; do
    item=$(trim "$item")
    if [[ -n "$item" ]]; then
      cycle+=("$item")
    fi
  done
  if [[ ${#cycle[@]} -eq 0 ]]; then
    echo "cycle_order is empty" >&2
    return 1
  fi
}

yaml_value() {
  local key=$1 file=$2 line
  line=$(grep -E "^${key}:[[:space:]]*[^[:space:]#]" "$file" | head -n 1 || true)
  if [[ -z "$line" ]]; then
    return 1
  fi
  line=${line#*:}
  line=${line%%#*}
  trim "$line"
}

setup_pythonpath() {
  local dir
  dir=$(script_dir)
  if [[ -d "${dir}/skip_htpc" ]]; then
    export PYTHONPATH="${dir}${PYTHONPATH:+:$PYTHONPATH}"
  elif [[ -d /usr/local/share/skip-htpc/skip_htpc ]]; then
    export PYTHONPATH="/usr/local/share/skip-htpc${PYTHONPATH:+:$PYTHONPATH}"
  fi
}

pick_browser() {
  if [[ -n "${SKIP_HTPC_BROWSER:-}" ]]; then
    printf '%s\n' "$SKIP_HTPC_BROWSER"
    return
  fi
  local name
  # Chrome ships Widevine. Chromium is accepted only when Chrome is absent.
  for name in google-chrome-stable google-chrome chromium chromium-browser; do
    if command -v "$name" >/dev/null 2>&1; then
      command -v "$name"
      return
    fi
  done
  return 1
}

state_dir() {
  if [[ -n "${SKIP_HTPC_STATE:-}" ]]; then
    printf '%s\n' "$SKIP_HTPC_STATE"
    return
  fi
  if [[ -n "${XDG_STATE_HOME:-}" ]]; then
    printf '%s\n' "${XDG_STATE_HOME}/skip-htpc"
    return
  fi
  printf '%s\n' "${HOME}/.local/state/skip-htpc"
}

read_last() {
  local path
  path="$(state_dir)/last-app"
  if [[ -f "$path" ]]; then
    tr -d '[:space:]' < "$path"
  fi
}

write_last() {
  local dir
  dir=$(state_dir)
  mkdir -p "$dir"
  printf '%s\n' "$1" > "${dir}/last-app"
}

debounced() {
  local interval=${SKIP_HTPC_DEBOUNCE:-0.35}
  if [[ "$interval" == "0" ]]; then
    return 1
  fi
  local dir path now prev
  dir=$(state_dir)
  mkdir -p "$dir"
  path="${dir}/debounce-next"
  now=$(date +%s%N)
  if [[ -f "$path" ]]; then
    prev=$(tr -d '[:space:]' < "$path" || echo 0)
    # interval is seconds. Compare in nanoseconds with awk-free integer math.
    # 0.35 -> 350000000. Only the default and whole seconds are required.
    local threshold=350000000
    case "$interval" in
      0.35) threshold=350000000 ;;
      *) threshold=$((interval * 1000000000)) ;;
    esac
    if [[ "$prev" =~ ^[0-9]+$ ]] && (( now - prev < threshold )); then
      return 0
    fi
  fi
  printf '%s\n' "$now" > "$path"
  return 1
}

current_app() {
  if ! command -v wmctrl >/dev/null 2>&1; then
    return 0
  fi
  local id desktop class rest
  while read -r id desktop class rest; do
    case "$class" in
      Kodi|kodi|*.Kodi|*.kodi)
        printf '%s\n' kodi
        return 0
        ;;
      *skip-htpc-netflix*|*Skip-htpc-netflix*)
        printf '%s\n' netflix
        return 0
        ;;
      *skip-htpc-areena*|*Skip-htpc-areena*)
        printf '%s\n' areena
        return 0
        ;;
    esac
  done < <(wmctrl -lx 2>/dev/null || true)
}

next_app() {
  local current=$1 i
  if [[ -z "$current" ]]; then
    printf '%s\n' "${cycle[0]}"
    return
  fi
  for i in "${!cycle[@]}"; do
    if [[ "${cycle[$i]}" == "$current" ]]; then
      printf '%s\n' "${cycle[$(( (i + 1) % ${#cycle[@]} ))]}"
      return
    fi
  done
  printf '%s\n' "${cycle[0]}"
}

start_line() {
  local id=$1 browser
  browser=$(pick_browser || true)
  case "$id" in
    kodi) printf '%s\n' "kodi" ;;
    netflix) printf '%s\n' "${browser:-google-chrome} --app=${netflix_url}" ;;
    areena) printf '%s\n' "${browser:-google-chrome} --app=${areena_url}" ;;
    *) echo "unknown app ${id}" >&2; return 2 ;;
  esac
}

require_display() {
  if [[ "${SKIP_HTPC_DRY:-}" == 1 ]]; then
    return
  fi
  if [[ -z "${DISPLAY:-}" ]]; then
    echo "DISPLAY is not set" >&2
    exit 1
  fi
}

start_app() {
  local id=$1
  if [[ "${SKIP_HTPC_DRY:-}" == 1 ]]; then
    start_line "$id"
    write_last "$id"
    return
  fi
  require_display
  setup_pythonpath
  export SKIP_HTPC_NETFLIX_URL="$netflix_url"
  export SKIP_HTPC_AREENA_URL="$areena_url"
  python3 -m skip_htpc launch "$id"
  write_last "$id"
}

load_urls() {
  local file
  file=$(config_file)
  if [[ ! -f "$file" ]]; then
    echo "missing config: ${file}" >&2
    return 1
  fi
  read_cycle_order "$file"
  netflix_url=$(yaml_value netflix_url "$file" || true)
  areena_url=$(yaml_value areena_url "$file" || true)
  netflix_url=${netflix_url:-$NETFLIX_URL_DEFAULT}
  areena_url=${areena_url:-$AREENA_URL_DEFAULT}
}

usage() {
  echo "usage: launch.sh kodi|netflix|areena|next|status" >&2
}

main() {
  local cmd=${1:-}
  if [[ -z "$cmd" || "$cmd" == "-h" || "$cmd" == "--help" ]]; then
    usage
    [[ -n "$cmd" ]]
    return
  fi
  load_urls
  case "$cmd" in
    kodi|netflix|areena)
      start_app "$cmd"
      ;;
    next)
      if debounced; then
        return 0
      fi
      local last focused current target
      last=$(read_last || true)
      focused=$(current_app || true)
      current=${focused:-$last}
      target=$(next_app "$current")
      echo "next: ${target}"
      start_app "$target"
      ;;
    status)
      local browser last focused
      browser=$(pick_browser || true)
      last=$(read_last || true)
      focused=$(current_app || true)
      echo "cycle_order: ${cycle[*]}"
      echo "focused: ${focused:-none}"
      echo "last: ${last:-none}"
      echo "browser: ${browser:-missing}"
      echo "netflix: ${netflix_url}"
      echo "areena: ${areena_url}"
      ;;
    *)
      usage
      return 2
      ;;
  esac
}

main "$@"
