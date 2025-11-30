#!/bin/bash
################################################################################
# DIAKEN RPM BUILD SCRIPT
# Version: 2.3.6
# Description: Build RPM package for Diaken
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

VERSION="2.3.6"
RELEASE="1"
NAME="diaken"
BUILD_DIR="$HOME/rpmbuild"

print_header() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}     ${BOLD}DIAKEN RPM BUILD SCRIPT${NC}                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}     Version $VERSION                                          ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

check_dependencies() {
    print_info "Checking build dependencies..."
    
    local deps=("rpm-build" "rpmdevtools" "git")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null && ! rpm -q "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing dependencies: ${missing[*]}"
        echo "Install with: sudo dnf install ${missing[*]}"
        exit 1
    fi
    
    print_success "All dependencies installed"
}

setup_build_environment() {
    print_info "Setting up build environment..."
    
    # Create RPM build directory structure
    rpmdev-setuptree
    
    # Clean previous builds
    rm -rf "$BUILD_DIR/SOURCES/$NAME-$VERSION"
    rm -f "$BUILD_DIR/SOURCES/$NAME-$VERSION.tar.gz"
    rm -f "$BUILD_DIR/SRPMS/$NAME-$VERSION-$RELEASE"*.src.rpm
    rm -f "$BUILD_DIR/RPMS/noarch/$NAME-$VERSION-$RELEASE"*.noarch.rpm
    
    print_success "Build environment ready"
}

prepare_source() {
    print_info "Preparing source files..."
    
    # Create source directory
    mkdir -p "$BUILD_DIR/SOURCES/$NAME-$VERSION"
    
    # Copy application files (excluding .git, venv, etc.)
    rsync -av \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='staticfiles' \
        --exclude='media' \
        --exclude='*.log' \
        --exclude='db.sqlite3' \
        --exclude='.env' \
        ./ "$BUILD_DIR/SOURCES/$NAME-$VERSION/"
    
    # Create tarball
    cd "$BUILD_DIR/SOURCES"
    tar czf "$NAME-$VERSION.tar.gz" "$NAME-$VERSION"
    
    print_success "Source tarball created"
}

copy_spec_file() {
    print_info "Copying spec file..."
    
    cp diaken.spec "$BUILD_DIR/SPECS/"
    
    print_success "Spec file copied"
}

build_rpm() {
    print_info "Building RPM package..."
    
    cd "$BUILD_DIR/SPECS"
    rpmbuild -ba diaken.spec
    
    print_success "RPM package built"
}

show_results() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}     ${BOLD}BUILD COMPLETED SUCCESSFULLY!${NC}                        ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}RPM Package:${NC}"
    ls -lh "$BUILD_DIR/RPMS/noarch/$NAME-$VERSION-$RELEASE"*.noarch.rpm
    echo ""
    echo -e "${BOLD}Source RPM:${NC}"
    ls -lh "$BUILD_DIR/SRPMS/$NAME-$VERSION-$RELEASE"*.src.rpm
    echo ""
    echo -e "${BOLD}Installation:${NC}"
    echo -e "  ${CYAN}sudo dnf install $BUILD_DIR/RPMS/noarch/$NAME-$VERSION-$RELEASE.*.noarch.rpm${NC}"
    echo ""
    echo -e "${BOLD}After installation, run:${NC}"
    echo -e "  ${CYAN}sudo /usr/local/bin/diaken-install${NC}"
    echo ""
}

main() {
    print_header
    
    check_dependencies
    setup_build_environment
    prepare_source
    copy_spec_file
    build_rpm
    show_results
}

main "$@"
