--获取Lock标识
local lockkey = KEYS[1]
--获取owner标识
local owner = ARGV[1]

--解锁操作返回值:
--      > 0完成:1解锁成功;
--      <=0错误:0锁不存在;-1拥有者错误;-2解锁错误;

--需要先判断锁的拥有者
local rc=redis.call('get',lockkey)

--锁不存在,直接返回
if  not rc then return 0 end

--当前不是锁的拥有者,直接返回
if rc ~= owner then return -1 end

--执行删除动作
if redis.call('del',lockkey)==1 then
    return 1        --锁删除成功
else
    return -2       --锁删除错误
end
