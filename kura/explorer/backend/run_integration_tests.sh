#!/bin/bash

# Kura Explorer Integration Tests
# Tests cluster-conversation mappings using real checkpoint data

set -e  # Exit on any error

echo "🔍 Kura Explorer Integration Tests"
echo "================================="
echo "Testing cluster-conversation mappings with real data"
echo ""

# Set up environment  
export PYTHONPATH="/Users/jasonliu/dev/kura:$PYTHONPATH"
export KURA_CHECKPOINT_DIR="/Users/jasonliu/dev/kura/tutorial_checkpoints"

# Change to backend directory
cd "$(dirname "$0")"

echo "📍 Current directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo "📁 Checkpoint dir: $KURA_CHECKPOINT_DIR"
echo ""

# Check if checkpoint directory exists
if [ ! -d "$KURA_CHECKPOINT_DIR" ]; then
    echo "❌ Checkpoint directory not found: $KURA_CHECKPOINT_DIR"
    echo "Please ensure the tutorial checkpoints are available."
    exit 1
fi

echo "✅ Checkpoint directory found"
echo ""

# Function to run test categories
run_test_category() {
    local description="$1"
    local test_file="$2"
    local test_class="$3"
    
    echo "🔄 $description"
    echo "   File: $test_file"
    echo "   Class: $test_class"
    
    if uv run pytest "$test_file::$test_class" -v -s; then
        echo "✅ $description - PASSED"
    else
        echo "❌ $description - FAILED"
        return 1
    fi
    echo ""
}

echo "🚀 Starting integration tests..."
echo ""

# Database integrity tests
run_test_category "Database Schema Validation" \
    "tests/test_database_integrity.py" \
    "TestDatabaseSchema"

run_test_category "Data Loading Verification" \
    "tests/test_database_integrity.py" \
    "TestDataLoading"

run_test_category "Database Relationships" \
    "tests/test_database_integrity.py" \
    "TestClusterConversationRelationships"

# Cluster mapping tests
run_test_category "Cluster-Conversation Mapping" \
    "tests/test_integration_clusters.py" \
    "TestClusterConversationMapping"

run_test_category "API Endpoint Integration" \
    "tests/test_integration_clusters.py" \
    "TestClusterAPIEndpoints"

run_test_category "Data Integrity Checks" \
    "tests/test_integration_clusters.py" \
    "TestDataIntegrity"

# Optional: Search integration (may not work if conversations are empty)
echo "🔄 Search Integration (Optional)"
if uv run pytest "tests/test_integration_clusters.py::TestSearchIntegration" -v -s; then
    echo "✅ Search Integration - PASSED"
else
    echo "⚠️  Search Integration - FAILED (may be expected if no conversation content)"
fi
echo ""

echo "📊 Running comprehensive database check..."
echo ""

# Run a comprehensive check that shows the current state
uv run python3 -c "
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

os.environ['KURA_CHECKPOINT_DIR'] = '/Users/jasonliu/dev/kura/tutorial_checkpoints'

from kura.explorer.api import KuraExplorer
from sqlmodel import Session, select, func
from kura.explorer.db.models import ClusterDB, ConversationDB, ClusterConversationLink, SummaryDB

print('📈 Current Database State:')
print('=' * 40)

try:
    explorer = KuraExplorer('/Users/jasonliu/dev/kura/tutorial_checkpoints')
    
    with Session(explorer.engine) as session:
        # Count records
        conv_count = session.exec(select(func.count(ConversationDB.chat_id))).one()
        summary_count = session.exec(select(func.count(SummaryDB.chat_id))).one()
        cluster_count = session.exec(select(func.count(ClusterDB.id))).one()
        link_count = session.exec(select(func.count(ClusterConversationLink.cluster_id))).one()
        
        print(f'Conversations: {conv_count:,}')
        print(f'Summaries: {summary_count:,}')
        print(f'Clusters: {cluster_count:,}')
        print(f'Links: {link_count:,}')
        print()
        
        # Test a specific cluster
        cluster = session.exec(select(ClusterDB).limit(1)).first()
        if cluster:
            cluster_convs = session.exec(
                select(func.count(ClusterConversationLink.conversation_id))
                .where(ClusterConversationLink.cluster_id == cluster.id)
            ).one()
            print(f'Sample cluster \"{cluster.name}\" has {cluster_convs} conversations')
            
            # Test API access
            cluster_detail = explorer.get_cluster(cluster.id)
            if cluster_detail:
                api_count = cluster_detail.conversation_count
                loaded_count = len(cluster_detail.conversations) if hasattr(cluster_detail, 'conversations') and cluster_detail.conversations else 0
                print(f'API reports: {api_count} conversations')
                print(f'Loaded via relationship: {loaded_count} conversations')
                
                if loaded_count > 0:
                    print('✅ Cluster-conversation relationships working!')
                else:
                    print('⚠️  Cluster-conversation relationships need fixing')
            else:
                print('❌ Could not load cluster detail')
        else:
            print('❌ No clusters found')
            
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "📋 Integration Test Summary"
echo "=========================="
echo "✅ Database schema validated"
echo "✅ Data loading verified"  
echo "✅ Cluster-conversation mappings tested"
echo "✅ API endpoints validated with real data"
echo "✅ Data integrity checked"
echo ""
echo "🎯 These tests verify that:"
echo "   • Clusters are properly mapped to conversations"
echo "   • Database relationships work correctly"
echo "   • API endpoints return real conversation data"
echo "   • No orphaned records exist"
echo "   • Search functionality maps correctly"
echo ""
echo "📝 If any tests failed, check:"
echo "   1. Database loader creating conversation records"
echo "   2. SQLModel relationships configured correctly"
echo "   3. API methods using proper joins"
echo "   4. selectinload for eager loading relationships"
echo ""
echo "🎉 Integration testing complete!" 