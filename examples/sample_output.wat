(module
  (import "env" "print" (func $print (param i32)))
  (import "env" "print_f64" (func $print_f64 (param f64)))
  (import "env" "print_str" (func $print_str (param i32) (param i32)))
  (memory (export "memory") 1)
  (data (i32.const 0) "Hello from DODO!")
  (data (i32.const 16) "The answer is:")
  (data (i32.const 30) "That is a big number!")
  (data (i32.const 51) "That is a small number.")
  (func (export "main")
    (local $x i32)
    (local $y i32)
    (local $result i32)
    i32.const 0
    i32.const 16
    call $print_str
    i32.const 42
    local.set $x
    i32.const 8
    local.set $y
    local.get $x
    local.get $y
    i32.add
    local.set $result
    i32.const 16
    i32.const 14
    call $print_str
    local.get $result
    call $print
    local.get $result
    i32.const 40
    i32.gt_s
    if
    i32.const 30
    i32.const 21
    call $print_str
    else
    i32.const 51
    i32.const 23
    call $print_str
    end
  )
)
