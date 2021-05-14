# 修改代码
## 一、命名

1. 尽量不改变原来的命名习惯，依旧使用驼峰式命名法
2. 重新选择变量名，做到名副其实

## 二、函数

## 三、try catch

## 四、类
### 上传和删除文件类
upload和remove分别用在了input, output, speed, log, abnormal_input这几种文件里，用到时需要指定文件目录
### 参数类
目前写在了主函数里面，找找更好的位置
### 写文件类
在写入input, output, speed, abnormal_input时，都需要使用到这个类

相同地方：
+ 都有一个numpy的矩阵，调用np.savetxt()就将其写入到的文件中去了
+ 都需要指定文件的路径及名称
+ 考虑一个文件里放入多长时间的数据时，需要考虑文件未满的标志


## 五、整体架构
目前的运行原理是：
1. 在主函数里调用 receiveMatrixDataFun
2. 另外开始两个进程，分别运行estimate和upload

注意，如果除了receiveMatrixDataFun外，还将接收speed的数据写成了另外一个进程，要在代码的最后加入close的部分。

## 六、功能补充
1. 如何把check文件夹的大小，且写入日志的功能加上？++ 加入了！
2. 如何把时间戳给自动生成好？
3. 如何解决无法ctrl+C的问题？

# 七、常见问题

1.  [     git push 不用输入用户名和密码        ](https://www.cnblogs.com/YC-L/p/12353431.html)              

```
git config  credential.helper store      
```

2. 用git stash解决git pull时的冲突

   [more](https://blog.csdn.net/cswioodn/article/details/80812745)

3. 如何解决merge conflict的方法
首先在pull的时候加上rebase，解决conflict，最后push

    git pull --rebase origin remote

if there is conflict, clean it and execute the following command

    git add .
    git rebase --continue

if all be done

    git push origin remote





