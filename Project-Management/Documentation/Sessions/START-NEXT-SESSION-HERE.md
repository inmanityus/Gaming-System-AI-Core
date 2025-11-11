# Start Next Session Here

**Instance**: i-0bb470b51af7f8a7d ⚠️ PROTECTED  
**Database**: ai-consciousness-memory.cal6eoegigyq.us-east-1.rds.amazonaws.com  
**Password**: .cursor/db-password-PRIVATE.txt

---

## Quick Finish (15-30 min)

### SSH to instance:
```bash
aws ssm start-session --target i-0bb470b51af7f8a7d
```

### Start consciousness:
```bash
cd /home/ubuntu
export PYTHONPATH=/home/ubuntu
export CONSCIOUSNESS_DB_URL="postgresql://consciousness:PASSWORD@ai-consciousness-memory.cal6eoegigyq.us-east-1.rds.amazonaws.com:5432/postgres"
python3 -m consciousness.main
```

### If works → Make permanent

---

**Foundation complete. Just needs config. See COMPLETE-HANDOFF-FOR-NEXT-SESSION.md**


